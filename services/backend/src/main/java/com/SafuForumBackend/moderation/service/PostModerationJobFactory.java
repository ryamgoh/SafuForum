package com.SafuForumBackend.moderation.service;

import com.SafuForumBackend.moderation.entity.ModerationJobSpec;
import com.SafuForumBackend.moderation.enums.JobContentType;
import com.SafuForumBackend.post.entity.Post;
import org.springframework.stereotype.Component;

import java.util.ArrayList;
import java.util.List;

@Component
public class PostModerationJobFactory {

    public List<ModerationJobSpec> buildJobs(Post post) {
        List<ModerationJobSpec> jobs = new ArrayList<>();

        if (post.getTitle() != null && !post.getTitle().isBlank()) {
            jobs.add(new ModerationJobSpec("title", JobContentType.text, post.getTitle()));
        }

        if (post.getContent() != null && !post.getContent().isBlank()) {
            jobs.add(new ModerationJobSpec("content", JobContentType.text, post.getContent()));
        }

        if (post.getTags() != null && !post.getTags().isEmpty()) {
            post.getTags().forEach(tag -> {
                if (tag.getName() != null && !tag.getName().isBlank()) {
                    jobs.add(new ModerationJobSpec("tag:" + tag.getName(), JobContentType.text, tag.getName()));
                }
            });
        }

        if (post.getImages() != null && !post.getImages().isEmpty()) {
            post.getImages().forEach(image -> {
                if (image.getSeaweedfsUrl() != null && !image.getSeaweedfsUrl().isBlank()) {
                    jobs.add(new ModerationJobSpec("image:" + image.getId(), JobContentType.image,
                            image.getSeaweedfsUrl()));
                }
            });
        }

        return jobs;
    }
}
