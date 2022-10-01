/**
 * Add image dimensions.
 */
ALTER TABLE Project
    ADD COLUMN image_width INT
    DEFAULT 512
    NOT NULL;
ALTER TABLE Project
    ADD COLUMN image_height INT
    DEFAULT 512
    NOT NULL;
