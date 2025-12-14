package com.SafuForumBackend.config;

import org.springframework.amqp.core.Binding;
import org.springframework.amqp.core.BindingBuilder;
import org.springframework.amqp.core.Queue;
import org.springframework.amqp.core.TopicExchange;
import org.springframework.amqp.support.converter.MessageConverter;
import org.springframework.amqp.support.converter.SimpleMessageConverter;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import java.util.List;

@Configuration
public class RabbitMQConfig {

    public static final String EVENT_EXCHANGE = "safu.event.exchange";

    public static final String VOTE_REPUTATION_QUEUE = "vote.reputation.queue";

    public static final String VOTE_ROUTING_KEY = "vote.*";

    @Bean
    public TopicExchange eventExchange() {
        return new TopicExchange(EVENT_EXCHANGE);
    }

    @Bean
    public Queue voteReputationQueue() {
        return new Queue(VOTE_REPUTATION_QUEUE, true);
    }

    @Bean
    public Binding voteReputationBinding(Queue voteReputationQueue, TopicExchange eventExchange) {
        return BindingBuilder.bind(voteReputationQueue)
                .to(eventExchange)
                .with(VOTE_ROUTING_KEY);
    }

    @Bean
    public MessageConverter messageConverter() {
        SimpleMessageConverter converter = new SimpleMessageConverter();
        converter.setAllowedListPatterns(
                List.of(
                        "com.SafuForumBackend.*",
                        "java.util.*",
                        "java.lang.*"
                )
        );
        return converter;
    }
}
