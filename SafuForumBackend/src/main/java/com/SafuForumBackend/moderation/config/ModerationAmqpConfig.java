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
    public DirectExchange moderationResultExchange() {
        return new DirectExchange(properties.getResultExchange(), true, false);
    }

    @Bean
    public Queue moderationJobCompletedQueue() {
        return new Queue(properties.getQueues().getJobCompleted(), true);
    }

    @Bean
    public Binding moderationJobCompletedBinding(Queue moderationJobCompletedQueue,
            TopicExchange moderationIngressExchange) {
        return BindingBuilder.bind(moderationJobCompletedQueue)
                .to(moderationIngressExchange)
                .with(properties.getRouting().getJobCompleted());
    }

    @Bean
    public Binding moderationJobResultBinding(Queue moderationJobCompletedQueue,
            DirectExchange moderationResultExchange) {
        return BindingBuilder.bind(moderationJobCompletedQueue)
                .to(moderationResultExchange)
                .with(properties.getRouting().getJobResult());
    }
}
