/**
 * A list of all database versions successfully migrated to.
 */
CREATE TABLE Migrations (
    /**
     * The database version.
     */
    version INT
);


/**
 * A project.
 */
CREATE TABLE Project (
    /**
     * The unique ID of this project.
     */
    id BLOB
        PRIMARY KEY
        ON CONFLICT ROLLBACK,

    /**
     * The name of this project.
     */
    name TEXT,

    /**
     * A short description.
     */
    description TEXT
);


CREATE TABLE Prompt (
    /**
     * The unique ID of this prompt.
     */
    id BLOB
        PRIMARY KEY
        ON CONFLICT ROLLBACK,

    /**
     * The project containing this prompt.
     */
    project BLOB
        REFERENCES Project
        ON DELETE CASCADE,

    /**
     * The prompt text.
     */
    text TEXT
);


CREATE TABLE Image (
    /**
     * The unique ID of this image.
     */
    id BLOB
        PRIMARY KEY
        ON CONFLICT ROLLBACK,

    /**
     * The UNIX timestamp of this image.
     *
     * We assume monotonically increasing values.
     */
    timestamp INTEGER
        DEFAULT NOW,

    /**
     * The content type of this image resource.
     */
    content_type TEXT,

    /**
     * The image data.
     */
    data BLOB
);


CREATE TABLE Prompt_Image (
    prompt BLOB
        REFERENCES Prompt
        ON DELETE CASCADE,
    image BLOB
        REFERENCES Image
        ON DELETE CASCADE
);
