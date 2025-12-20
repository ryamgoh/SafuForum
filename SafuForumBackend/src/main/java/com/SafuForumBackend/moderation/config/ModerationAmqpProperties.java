package com.SafuForumBackend.moderation.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "moderation.amqp")
public class ModerationAmqpProperties {

    private String ingressTopicExchange = "x.moderation.ingress";

    private final Routing routing = new Routing();
    private final Queues queues = new Queues();

    @Getter
    @Setter
    public static class Routing {
        private String textJob = "moderation.job.text";
        private String imageJob = "moderation.job.image";
        private String jobCompleted = "moderation.job.completed";
    }

    @Getter
    @Setter
    public static class Queues {
        private String jobCompleted = "q.moderation.job.completed";
    }
}
