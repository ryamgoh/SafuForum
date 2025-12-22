package com.SafuForumBackend.moderation.config;

import lombok.RequiredArgsConstructor;
import org.springframework.amqp.core.*;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
@RequiredArgsConstructor
public class ModerationAmqpConfig {

    private final ModerationAmqpProperties properties;

    @Bean
    public TopicExchange moderationIngressExchange() {
        return new TopicExchange(properties.getIngressExchange(), true, false);
    }

    @Bean
    public TopicExchange moderationEgressExchange() {
        return new TopicExchange(properties.getEgressExchange(), true, false);
    }

    @Bean
    public Queue moderationJobCompletedQueue() {
        return new Queue(properties.getQueues().getJobCompleted(), true);
    }

    @Bean
    public Binding moderationJobCompletedBinding(Queue moderationJobCompletedQueue,
            TopicExchange moderationEgressExchange) {
        return BindingBuilder.bind(moderationJobCompletedQueue)
                .to(moderationEgressExchange)
                .with(properties.getRouting().getJobCompleted());
    }
}
