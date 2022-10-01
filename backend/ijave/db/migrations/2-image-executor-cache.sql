CREATE TABLE ImageExecutorCache (
    /**
     * The prompt to which this cache data belongs.
     */
    id BLOB
        PRIMARY KEY
        REFERENCES Prompt
        ON DELETE CASCADE,

    /**
     * The step for which the previous data was generated.
     */
    step INT,

    /**
     * The total number of steps.
     */
    steps INT,

    /**
     * The strength of the transform.
     */
    strength FLOAT,

    /**
     * The previous encoded data.
     */
    latent BLOB
);
