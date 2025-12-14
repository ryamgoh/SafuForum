package com.SafuForumBackend.reputation.service;

import com.SafuForumBackend.config.RabbitMQConfig;
import com.SafuForumBackend.user.entity.User;
import com.SafuForumBackend.user.repository.UserRepository;
import com.SafuForumBackend.vote.event.VoteEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
@RequiredArgsConstructor
@Slf4j
public class ReputationService {

    private final UserRepository userRepository;

    @RabbitListener(queues = RabbitMQConfig.VOTE_REPUTATION_QUEUE)
    @Transactional
    public void handleVoteEvent(VoteEvent event) {
        User author = userRepository.findById(event.authorId())
                .orElseThrow(() -> new IllegalArgumentException("User not found with id: " + event.authorId()));
        int currentReputation = author.getReputation();
        int updatedReputation = currentReputation + event.voteDelta();
        if (updatedReputation < 0) {
            updatedReputation = 0;
        }
        author.setReputation(updatedReputation);
        userRepository.save(author);
        log.info("Updated reputation for user {}: {} -> {}", author.getId(), currentReputation, updatedReputation);
    }
}
