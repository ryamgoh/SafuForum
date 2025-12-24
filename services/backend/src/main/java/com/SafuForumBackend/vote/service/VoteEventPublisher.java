package com.SafuForumBackend.vote.service;

import com.SafuForumBackend.config.RabbitMQConfig;
import com.SafuForumBackend.vote.event.VoteEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.stereotype.Service;

@Service
@RequiredArgsConstructor
@Slf4j
public class VoteEventPublisher {

    private final RabbitTemplate rabbitTemplate;

    public void sendMessage(VoteEvent voteEvent) {
        log.info("Publishing vote event for author {} on {} {}",
                voteEvent.authorId(),
                voteEvent.entityType(),
                voteEvent.entityId());
        rabbitTemplate.convertAndSend(RabbitMQConfig.EVENT_EXCHANGE,
                "vote." + voteEvent.entityType().name().toLowerCase(), voteEvent);

    }
}
