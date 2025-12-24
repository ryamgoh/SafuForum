package com.SafuForumBackend.tag.controller;

import com.SafuForumBackend.tag.dto.TagResponse;
import com.SafuForumBackend.tag.entity.Tag;
import com.SafuForumBackend.tag.repository.TagRepository;
import lombok.RequiredArgsConstructor;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/tags")
@RequiredArgsConstructor
public class TagController {

    private final TagRepository tagRepository;

    @GetMapping
    public ResponseEntity<List<TagResponse>> getAllTags() {
        List<Tag> tags = tagRepository.findAll();

        List<TagResponse> tagsWithCount = tags.stream()
                .map(tag -> new TagResponse(
                        tag.getId(),
                        tag.getName(),
                        tag.getSlug(),
                        tag.getColor(),
                        tagRepository.countPostsByTagId(tag.getId())
                ))
                .collect(Collectors.toList());

        return ResponseEntity.ok(tagsWithCount);
    }

    @GetMapping("/{slug}")
    public ResponseEntity<Tag> getTagBySlug(@PathVariable String slug) {
        Tag tag = tagRepository.findBySlug(slug)
                .orElseThrow(() -> new RuntimeException("Tag not found"));
        return ResponseEntity.ok(tag);
    }
}