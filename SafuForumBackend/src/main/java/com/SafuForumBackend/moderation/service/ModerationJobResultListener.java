package com.SafuForumBackend.moderation.service;

import com.SafuForumBackend.moderation.entity.ModerationJob;
import com.SafuForumBackend.moderation.enums.ModerationStatus;
import com.SafuForumBackend.moderation.event.ModerationJobResultEvent;
import com.SafuForumBackend.moderation.repository.ModerationJobRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.amqp.support.AmqpHeaders;
import org.springframework.messaging.handler.annotation.Header;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

import java.nio.charset.StandardCharsets;
import java.time.LocalDateTime;

@Component
@RequiredArgsConstructor
@Slf4j
public class ModerationJobResultListener {

    private final ModerationJobRepository moderationJobRepository;

    @RabbitListener(queues = "${moderation.amqp.queues.results-backend}")
    @Transactional
    public void handleModerationJobResult(
            ModerationJobResultEvent event,
            @Header(name = AmqpHeaders.CORRELATION_ID, required = false) Object correlationId) {
        Long jobId = resolveJobId(event, correlationId);
        if (jobId == null) {
            log.warn("Received moderation job result with no jobId/correlationId; ignoring");
            return;
        }

        ModerationJob job = moderationJobRepository.findById(jobId).orElse(null);
        if (job == null) {
            log.warn("Received moderation job result for unknown jobId={}; ignoring", jobId);
            return;
        }

        if (job.getStatus() != ModerationStatus.pending) {
            return;
        }

        Integer currentPostVersion = job.getPost().getVersion();
        if (currentPostVersion != null && !currentPostVersion.equals(job.getPostVersion())) {
            log.info("Ignoring stale moderation result for jobId={} postId={} jobPostVersion={} currentPostVersion={}",
                    job.getId(),
                    job.getPost().getId(),
                    job.getPostVersion(),
                    currentPostVersion);
            return;
        }

        if (event.status() == null) {
            log.warn("Received moderation job result for jobId={} with null status; ignoring", jobId);
            return;
        }

        job.setStatus(event.status());
        job.setErrorMessage(event.errorMessage());
        job.setUpdatedAt(LocalDateTime.now());
        moderationJobRepository.save(job);
    }

    private Long resolveJobId(ModerationJobResultEvent event, Object correlationId) {
        if (event != null && event.moderationJobId() != null) {
            return event.moderationJobId();
        }
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
