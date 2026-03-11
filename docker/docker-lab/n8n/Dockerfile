FROM docker.n8n.io/n8nio/n8n
USER root

# Install community node in n8n's custom extensions directory
RUN mkdir -p /home/node/.n8n/nodes && \
    cd /home/node/.n8n/nodes && \
    npm install n8n-nodes-checkmk && \
    chown -R node:node /home/node/.n8n/nodes

USER node
