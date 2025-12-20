package com.SafuForumBackend.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;

import java.net.URI;

@Configuration
public class S3Config {

    @Value("${seaweedfs.s3.endpoint:http://seaweed-s3:8333}")
    private String s3Endpoint;

    @Value("${seaweedfs.s3.access-key:dev}")
    private String accessKey;

    @Value("${seaweedfs.s3.secret-key:dev}")
    private String secretKey;

    @Value("${seaweedfs.s3.bucket-name:safu-forum-images}")
    private String bucketName;

    @Bean
    public S3Client s3Client() {
        AwsBasicCredentials credentials = AwsBasicCredentials.create(accessKey, secretKey);

        return S3Client.builder()
                .endpointOverride(URI.create(s3Endpoint))
                .credentialsProvider(StaticCredentialsProvider.create(credentials))
                .region(Region.US_EAST_1)
                .forcePathStyle(true)
                .build();
    }

    public String getBucketName() {
        return bucketName;
    }
}