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
    public DirectExchange moderationResultsExchange() {
        return new DirectExchange(properties.getResultsExchange(), true, false);
    }

    @Bean
    public TopicExchange moderationDecisionsExchange() {
        return new TopicExchange(properties.getDecisionsExchange(), true, false);
    }

    @Bean
    public Queue moderationResultsBackendQueue() {
        return new Queue(properties.getQueues().getResultsBackend(), true);
    }

    @Bean
    public Binding moderationResultsBackendBinding(Queue moderationResultsBackendQueue,
            DirectExchange moderationResultsExchange) {
        return BindingBuilder.bind(moderationResultsBackendQueue)
                .to(moderationResultsExchange)
                .with(properties.getRouting().getJobResult());
    }

    @Bean
    public Queue moderationNotifyQueue() {
        return new Queue(properties.getQueues().getNotify(), true);
    }

    @Bean
    public Binding moderationNotifyBinding(Queue moderationNotifyQueue, TopicExchange moderationDecisionsExchange) {
        return BindingBuilder.bind(moderationNotifyQueue)
                .to(moderationDecisionsExchange)
                .with(properties.getRouting().getPostCompleted());
    }
}
