package com.SafuForumBackend.moderation.config;

import lombok.Getter;
import lombok.Setter;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

import java.time.Duration;

@Getter
@Setter
@Component
@ConfigurationProperties(prefix = "moderation.orchestrator")
public class ModerationOrchestratorProperties {

    private Duration jobTimeout = Duration.ofMinutes(10);
    private Duration timeoutCheckInterval = Duration.ofMinutes(1);
}

