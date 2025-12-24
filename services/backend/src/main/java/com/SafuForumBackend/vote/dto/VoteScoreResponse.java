package com.SafuForumBackend.vote.dto;

import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;

@Data
@NoArgsConstructor
@AllArgsConstructor
public class VoteScoreResponse {
    private Integer score;
    private Short userVote; // null if user hasn't voted, 1 or -1 if they have
}