package com.SafuForumBackend.moderation.service;

import com.SafuForumBackend.moderation.config.ModerationOrchestratorProperties;
import com.SafuForumBackend.moderation.entity.ModerationJob;
import com.SafuForumBackend.moderation.enums.ModerationStatus;
import com.SafuForumBackend.moderation.repository.ModerationJobRepository;
import com.SafuForumBackend.post.entity.Post;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;

@Component
@RequiredArgsConstructor
@Slf4j
public class ModerationTimeoutScheduler {

    private final ModerationJobRepository moderationJobRepository;
    private final ModerationOrchestratorProperties properties;

    @Scheduled(fixedDelayString = "#{@moderationOrchestratorProperties.timeoutCheckInterval.toMillis()}")
    @Transactional
    public void failTimedOutJobs() {
        LocalDateTime cutoff = LocalDateTime.now().minus(properties.getJobTimeout());
        List<ModerationJob> timedOutJobs = moderationJobRepository
                .findByStatusAndCreatedAtBefore(ModerationStatus.pending, cutoff);
        if (timedOutJobs.isEmpty()) {
            return;
        }

        LocalDateTime now = LocalDateTime.now();
        for (ModerationJob job : timedOutJobs) {
            Post post = job.getPost();
            Integer currentPostVersion = post.getVersion();

            job.setStatus(ModerationStatus.failed);
            job.setUpdatedAt(now);

            if (currentPostVersion != null && !currentPostVersion.equals(job.getPostVersion())) {
                job.setErrorMessage("Superseded by post version " + currentPostVersion);
                continue;
            }

            job.setErrorMessage("Timed out waiting for moderation result");
            if (post.getStatus() == ModerationStatus.pending) {
                post.setStatus(ModerationStatus.failed);
            }
        }

        moderationJobRepository.saveAll(timedOutJobs);
        log.warn("Marked {} moderation jobs as failed due to timeout", timedOutJobs.size());
    }
}
