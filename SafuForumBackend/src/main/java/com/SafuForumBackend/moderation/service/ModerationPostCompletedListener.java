package com.SafuForumBackend.moderation.service;

import com.SafuForumBackend.moderation.event.ModerationPostCompletedEvent;
import com.SafuForumBackend.post.entity.Post;
import com.SafuForumBackend.post.repository.PostRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Component;
import org.springframework.transaction.annotation.Transactional;

@Component
@RequiredArgsConstructor
@Slf4j
public class ModerationPostCompletedListener {

    private final PostRepository postRepository;

    @RabbitListener(queues = "${moderation.amqp.queues.notify}")
    @Transactional
    public void handleModerationPostCompleted(ModerationPostCompletedEvent event) {
        if (event.postId() == null || event.postVersion() == null || event.status() == null) {
            log.warn("Received moderation completion event with missing fields; ignoring");
            return;
        }

        Post post = postRepository.findById(event.postId()).orElse(null);
        if (post == null) {
            log.warn("Received moderation completion for unknown postId={}; ignoring", event.postId());
            return;
        }

        if (!event.postVersion().equals(post.getVersion())) {
            log.info("Ignoring stale moderation completion for postId={} eventVersion={} currentVersion={}",
                    event.postId(),
                    event.postVersion(),
                    post.getVersion());
            return;
        }

        post.setStatus(event.status());
        postRepository.save(post);
    }
}
