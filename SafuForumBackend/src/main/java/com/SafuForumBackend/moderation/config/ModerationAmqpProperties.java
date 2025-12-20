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

    private String ingressExchange = "safu.moderation.ingress";
    private String resultsExchange = "safu.moderation.results";
    private String decisionsExchange = "safu.moderation.decisions";

    private final Routing routing = new Routing();
    private final Queues queues = new Queues();

    @Getter
    @Setter
    public static class Routing {
        private String textJob = "moderation.job.text";
        private String imageJob = "moderation.job.image";
        private String jobResult = "moderation.job.result";
        private String postCompleted = "moderation.post.completed";
    }

    @Getter
    @Setter
    public static class Queues {
        private String resultsBackend = "safu.moderation.results.backend";
        private String notify = "safu.moderation.notify";
    }
}

