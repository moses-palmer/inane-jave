FROM python:3.8-slim

##
# The UID for the user inside the container.
ARG UID


##
# The prefix inside the container.
ENV PREFIX="/opt/inane-jave"


##
# This is where projects are kept.
ENV IJAVE_PROJECT_DIR="$PREFIX/projects"


##
# Run as a specific user.
RUN adduser \
    --system \
    --uid $UID \
    --home "$PREFIX" \
    inane-jave


##
# Install dependencies.
COPY requirements.txt "$PREFIX"

RUN true \
    && pip install --requirement "$PREFIX/requirements.txt" \
    && rm -rf /root/.cache


##
# Copy the entrypoint and application last; these will change the most.
COPY entrypoint /
COPY backend "$PREFIX/backend"


USER inane-jave

ENTRYPOINT [ "/entrypoint" ]
