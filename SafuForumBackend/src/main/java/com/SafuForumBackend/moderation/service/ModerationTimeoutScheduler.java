package com.SafuForumBackend.moderation.service;

import com.SafuForumBackend.moderation.config.ModerationOrchestratorProperties;
import com.SafuForumBackend.moderation.entity.ModerationJob;
import com.SafuForumBackend.moderation.enums.ModerationStatus;
import com.SafuForumBackend.moderation.repository.ModerationJobRepository;
import com.SafuForumBackend.post.entity.Post;
import com.SafuForumBackend.post.repository.PostRepository;

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
    private final PostRepository postRepository;
    private final ModerationOrchestratorProperties properties;

    /**
     * Scheduled task that fails moderation jobs that have timed out.
     * 
     * Runs at a fixed delay defined by the timeoutCheckInterval property.
     * 
     * Transactional to ensure database operations are atomic.
     */
    @Scheduled(fixedDelayString = "#{@moderationOrchestratorProperties.timeoutCheckInterval.toMillis()}")
    @Transactional
    public void failAllTimedOutJobs() {
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

            job.setErrorMessage("Timed out waiting for moderation completion");
            if (post.getStatus() == ModerationStatus.pending) {
                post.setStatus(ModerationStatus.failed);
                post.setUpdatedAt(now);
                postRepository.save(post);
            }
        }

        moderationJobRepository.saveAll(timedOutJobs);
        log.warn("Marked {} moderation jobs as failed due to timeout", timedOutJobs.size());
    }
}
