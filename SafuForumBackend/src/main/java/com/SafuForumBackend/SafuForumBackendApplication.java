package com.SafuForumBackend;

import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.scheduling.annotation.EnableScheduling;

@SpringBootApplication
@EnableScheduling
public class SafuForumBackendApplication {

	public static void main(String[] args) {
		SpringApplication.run(SafuForumBackendApplication.class, args);
	}

}
