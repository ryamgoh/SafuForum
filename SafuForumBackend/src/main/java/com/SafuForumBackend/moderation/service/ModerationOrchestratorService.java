package com.SafuForumBackend.moderation.service;

import com.SafuForumBackend.moderation.config.ModerationAmqpProperties;
import com.SafuForumBackend.moderation.entity.ModerationJob;
import com.SafuForumBackend.moderation.entity.ModerationJobSpec;
import com.SafuForumBackend.moderation.enums.JobContentType;
import com.SafuForumBackend.moderation.enums.ModerationStatus;
import com.SafuForumBackend.moderation.event.ModerationJobRequestedEvent;
import com.SafuForumBackend.moderation.repository.ModerationJobRepository;
import com.SafuForumBackend.post.entity.Post;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Set;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
@Slf4j
public class ModerationOrchestratorService {

    private final ModerationJobRepository moderationJobRepository;
    private final RabbitTemplate rabbitTemplate;
    private final ModerationAmqpProperties amqpProperties;
    private final PostModerationJobFactory postModerationJobFactory;
    private final AfterCommitExecutor afterCommitExecutor;

    @Transactional
    public void enqueueModerationForPost(Post post, Integer supersededPostVersion) {
        if (post.getId() == null) {
            throw new IllegalArgumentException("Post must be persisted before moderation jobs are created.");
        }

        Integer postVersion = post.getVersion();
        if (postVersion == null) {
            throw new IllegalArgumentException("Post version must be set before moderation jobs are created.");
        }

        markSupersededPendingJobsAsFailed(post, supersededPostVersion);

        List<ModerationJob> savedJobs = createAndSaveJobsForPost(post, postVersion);

        afterCommitExecutor.run(() -> savedJobs.forEach(this::publishJobRequestedEventSafely));
    }

    /**
     * Creates and saves moderation jobs for the given post and version.
     * 
     * @param post        The post to create jobs for.
     * @param postVersion The version of the post.
     * @return
     */
    private List<ModerationJob> createAndSaveJobsForPost(Post post, Integer postVersion) {
        List<ModerationJobSpec> jobSpecs = postModerationJobFactory.buildJobs(post);
        if (jobSpecs.isEmpty()) {
            log.warn("No moderation job specs generated for postId={}", post.getId());
            return List.of();
        }

        // Fetch existing jobs for this post and version to avoid duplicates
        Set<JobKey> existingJobKeys = moderationJobRepository.findByPostIdAndPostVersion(post.getId(), postVersion)
                .stream()
                .map(job -> new JobKey(job.getSourceField(), job.getContentType()))
                .collect(Collectors.toSet());

        // Filter out job specs that already have corresponding jobs
        List<ModerationJob> newJobs = jobSpecs.stream()
                .filter(spec -> !existingJobKeys.contains(new JobKey(spec.sourceField(), spec.contentType())))
                .map(spec -> ModerationJob.builder()
                        .post(post)
                        .postVersion(postVersion)
                        .sourceField(spec.sourceField())
                        .contentType(spec.contentType())
                        .payload(spec.payload())
                        .status(ModerationStatus.pending)
                        .build())
                .toList();

        if (newJobs.isEmpty()) {
            return List.of();
        }

        return moderationJobRepository.saveAll(newJobs);
    }

    /**
     * Marks any pending moderation jobs for the given post and superseded version
     * as failed.
     * 
     * @param post                  The post whose jobs are to be updated.
     * @param supersededPostVersion The superseded post version.
     */
    private void markSupersededPendingJobsAsFailed(Post post, Integer supersededPostVersion) {
        // No action needed if there's no superseded version
        if (supersededPostVersion == null) {
            return;
        }
        if (supersededPostVersion.equals(post.getVersion())) {
            return;
        }

        moderationJobRepository.updateStatusForPostVersion(
                post.getId(),
                supersededPostVersion,
                ModerationStatus.pending,
                ModerationStatus.failed,
                "Superseded by post version " + post.getVersion(),
                LocalDateTime.now());
    }

    private void publishJobRequestedEventSafely(ModerationJob job) {
        try {
            publishJobRequestedEvent(job);
        } catch (RuntimeException ex) {
            log.error("Failed to publish moderation job event for jobId={} postId={} postVersion={}: {}",
                    job.getId(),
                    job.getPost().getId(),
                    job.getPostVersion(),
                    ex.getMessage(),
                    ex);
        }
    }

    private void publishJobRequestedEvent(ModerationJob job) {
        String routingKey = routingKeyFor(job.getContentType());
        ModerationJobRequestedEvent event = new ModerationJobRequestedEvent(
                job.getId(),
                job.getPost().getId(),
                job.getPostVersion(),
                job.getSourceField(),
                job.getContentType(),
                job.getPayload());

        rabbitTemplate.convertAndSend(amqpProperties.getIngressTopicExchange(), routingKey, event, message -> {
            message.getMessageProperties().setCorrelationId(job.getId().toString());
            message.getMessageProperties().setMessageId(job.getId().toString());
            return message;
        });
    }

    private String routingKeyFor(JobContentType contentType) {
        return switch (contentType) {
            case text -> amqpProperties.getRouting().getTextJob();
            case image -> amqpProperties.getRouting().getImageJob();
        };
    }

    private record JobKey(String sourceField, JobContentType contentType) {
    }
}
