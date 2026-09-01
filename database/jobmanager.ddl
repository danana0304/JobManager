CREATE TYPE application_status AS ENUM ('Applied', 'Interviewing', 'Rejected', 'Accepted');
CREATE TYPE user_type AS ENUM ('Admin', 'User');

CREATE TABLE IF NOT EXISTS Users (
    UserId SERIAL PRIMARY KEY,
    UserType user_type NOT NULL DEFAULT 'User',
    Email VARCHAR(255) NOT NULL UNIQUE,
    Phone VARCHAR(20),
    Address VARCHAR(255),
    Password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Skills (
    SkillId SERIAL PRIMARY KEY,
    Name VARCHAR(50) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS UserSkills (
    UserId INT NOT NULL REFERENCES Users(UserId) ON DELETE CASCADE,
    SkillId INT NOT NULL REFERENCES Skills(SkillId) ON DELETE CASCADE,
    PRIMARY KEY (UserId, SkillId)
);

CREATE TABLE IF NOT EXISTS Admins (
    AdminId SERIAL PRIMARY KEY,
    Email VARCHAR(255) NOT NULL UNIQUE,
    Phone VARCHAR(20),
    Company VARCHAR(255),
    Address VARCHAR(255),
    Password VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Postings (
    PostingId SERIAL PRIMARY KEY,
    Company VARCHAR(255) NOT NULL,
    Position VARCHAR(255) NOT NULL
);

CREATE TABLE IF NOT EXISTS Applications (
    PostingId INT NOT NULL REFERENCES Postings(PostingId) ON DELETE CASCADE,
    UserId INT NOT NULL REFERENCES Users(UserId) ON DELETE CASCADE,
    Status application_status NOT NULL DEFAULT 'Applied',
    PRIMARY KEY (PostingId, UserId)
);
