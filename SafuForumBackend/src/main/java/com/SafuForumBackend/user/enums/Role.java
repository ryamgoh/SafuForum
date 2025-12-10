package com.SafuForumBackend.user.enums;

public enum Role {
    USER(0),
    TRUSTED_USER(10),
    MODERATOR(50),
    ADMIN(100);

    private final int level;

    Role(int level) {
        this.level = level;
    }

    public int getLevel() {
        return level;
    }

    public boolean hasAuthority(Role requiredRole) {
        return this.level >= requiredRole.level;
    }
}