FROM mcr.microsoft.com/devcontainers/typescript-node:1-22-bookworm

# Pin here, not in .mcp.json. Bumping = rebuild image, not a broken hackathon morning.
ARG CLAUDE_CODE_VERSION=latest
ARG SHADCN_VERSION=4.13.1

ENV NPM_CONFIG_FUND=false
ENV NPM_CONFIG_AUDIT=false
ENV NPM_CONFIG_UPDATE_NOTIFIER=false

USER node

# Both binaries land in the image at build time.
# At runtime nothing is resolved from the network -> no `npx @latest` failures.
RUN npm install -g \
        @anthropic-ai/claude-code@${CLAUDE_CODE_VERSION} \
        shadcn@${SHADCN_VERSION} \
    && npm cache clean --force

RUN echo "alias cc='claude --dangerously-skip-permissions'" >> /home/node/.bashrc \
    && echo "alias ccr='claude --dangerously-skip-permissions --resume'" >> /home/node/.bashrc
