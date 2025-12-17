package com.SafuForumBackend.config;

import org.springframework.beans.factory.annotation.Value;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import software.amazon.awssdk.auth.credentials.AwsBasicCredentials;
import software.amazon.awssdk.auth.credentials.StaticCredentialsProvider;
import software.amazon.awssdk.regions.Region;
import software.amazon.awssdk.services.s3.S3Client;
import software.amazon.awssdk.services.s3.model.CreateBucketRequest;
import software.amazon.awssdk.services.s3.model.HeadBucketRequest;
import software.amazon.awssdk.services.s3.model.NoSuchBucketException;

import jakarta.annotation.PostConstruct;
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

    private S3Client s3Client;

    @Bean
    public S3Client s3Client() {
        AwsBasicCredentials credentials = AwsBasicCredentials.create(accessKey, secretKey);

        this.s3Client = S3Client.builder()
                .endpointOverride(URI.create(s3Endpoint))
                .credentialsProvider(StaticCredentialsProvider.create(credentials))
                .region(Region.US_EAST_1) // SeaweedFS doesn't care about region, but SDK requires it
                .forcePathStyle(true) // Required for S3-compatible services
                .build();

        return this.s3Client;
    }

    @PostConstruct
    public void initializeBucket() {
        try {
            // Check if bucket exists
            s3Client.headBucket(HeadBucketRequest.builder()
                    .bucket(bucketName)
                    .build());
            System.out.println("S3 bucket '" + bucketName + "' already exists");
        } catch (NoSuchBucketException e) {
            // Bucket doesn't exist, create it
            s3Client.createBucket(CreateBucketRequest.builder()
                    .bucket(bucketName)
                    .build());
            System.out.println("S3 bucket '" + bucketName + "' created successfully");
        } catch (Exception e) {
            System.err.println("Error initializing S3 bucket: " + e.getMessage());
            // Don't throw - let the app start even if S3 is unavailable
        }
    }

    public String getBucketName() {
        return bucketName;
    }
}