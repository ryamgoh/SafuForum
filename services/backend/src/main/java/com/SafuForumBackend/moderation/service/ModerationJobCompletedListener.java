package com.SafuForumBackend.moderation.service;

import com.SafuForumBackend.moderation.entity.ModerationJob;
import com.SafuForumBackend.moderation.enums.ModerationStatus;
import com.SafuForumBackend.moderation.event.ModerationJobCompletedEvent;
import com.SafuForumBackend.moderation.repository.ModerationJobRepository;
import com.SafuForumBackend.post.entity.Post;
import com.SafuForumBackend.post.repository.PostRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.core.Message;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;
import java.util.List;

/**
 * Listener for moderation job completion events.
 * 
 * Handles updating the status of moderation jobs and associated posts.
 */
@Component
@RequiredArgsConstructor
@Slf4j
public class ModerationJobCompletedListener {

    private final ModerationJobRepository moderationJobRepository;
    private final PostRepository postRepository;

    /**
     * Handles a moderation job completion event.
     * 
     * @param jobCompletionEvent The moderation job completion event.
     * @param correlationId      The correlation ID from the message header, if
     *                           available.
     */
    @RabbitListener(queues = "${moderation.amqp.queues.job-completed}")
    @Transactional
    public void handleJobCompleted(
            ModerationJobCompletedEvent jobCompletionEvent,
            Message message) {
        Object correlationId = null;
        if (message != null && message.getMessageProperties() != null) {
            correlationId = message.getMessageProperties().getCorrelationId();
        }
        Long jobId = resolveJobId(correlationId);
        if (jobId == null) {
            log.warn("Received moderation completion with no jobId/correlationId; ignoring");
            return;
        }

        ModerationJob matchedJob = moderationJobRepository.findById(jobId).orElse(null);
        if (matchedJob == null) {
            log.warn("Received moderation completion for unknown jobId={}; ignoring", jobId);
            return;
        }

        // Only process if still pending in database
        if (matchedJob.getStatus() != ModerationStatus.pending) {
            return;
        }

        Post post = matchedJob.getPost();
        Integer currentPostVersion = post.getVersion();
        if (currentPostVersion != null && !currentPostVersion.equals(matchedJob.getPostVersion())) {
            log.info(
                    "Ignoring stale moderation completion for jobId={} postId={} jobPostVersion={} currentPostVersion={}",
                    matchedJob.getId(),
                    post.getId(),
                    matchedJob.getPostVersion(),
                    currentPostVersion);
            return;
        }

        if (jobCompletionEvent.status() == null) {
            log.warn("Received moderation completion for jobId={} with null status; ignoring", jobId);
            return;
        }

        matchedJob.setStatus(jobCompletionEvent.status());
        matchedJob.setErrorMessage(jobCompletionEvent.reason());
        matchedJob.setUpdatedAt(LocalDateTime.now());
        moderationJobRepository.save(matchedJob);

        updatePostStatusIfReady(post.getId(), matchedJob.getPostVersion());
    }

    /**
     * Updates the post status if all moderation jobs for the given post and version
     * are completed.
     * 
     * @param postId
     * @param postVersion
     */
    private void updatePostStatusIfReady(Long postId, Integer postVersion) {
        List<ModerationJob> jobs = moderationJobRepository.findByPostIdAndPostVersion(postId, postVersion);
        if (jobs.isEmpty()) {
            return;
        }

        ModerationStatus status = aggregateStatus(jobs);
        if (status == ModerationStatus.pending) {
            return;
        }
        Post post = postRepository.findById(postId).orElse(null);
        if (post == null) {
            return;
        }
        if (!postVersion.equals(post.getVersion())) {
            return;
        }

        post.setStatus(status);
        postRepository.save(post);
    }

    private ModerationStatus aggregateStatus(List<ModerationJob> jobs) {
        // If any jobs are still pending, do not update the post status yet (wait for
        // all to complete)
        boolean anyPending = jobs.stream().anyMatch(job -> job.getStatus() == ModerationStatus.pending);
        if (anyPending) {
            return ModerationStatus.pending;
        }
        boolean anyFailed = jobs.stream().anyMatch(job -> job.getStatus() == ModerationStatus.failed);
        if (anyFailed) {
            return ModerationStatus.failed;
        }
        boolean anyRejected = jobs.stream().anyMatch(job -> job.getStatus() == ModerationStatus.rejected);
        if (anyRejected) {
            return ModerationStatus.rejected;
        }
        return ModerationStatus.approved;
    }

    /**
     * Resolves the moderation job ID from the event or correlation ID.
     * 
     * @param correlationId
     * @return
     */
    private Long resolveJobId(Object correlationId) {
        if (correlationId == null) {
            return null;
        }
        if (correlationId instanceof byte[] bytes) {
            return parseLongOrNull(new String(bytes, StandardCharsets.UTF_8));
        }
        return parseLongOrNull(correlationId.toString());
    }

    private Long parseLongOrNull(String value) {
        try {
            return Long.parseLong(value);
        } catch (RuntimeException ex) {
            return null;
        }
    }
}
