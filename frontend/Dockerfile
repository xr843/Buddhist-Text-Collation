# Default to upstream registries — China-mainland users can opt into
# faster mirrors via build args:
#   docker build \
#     --build-arg NODE_IMAGE=swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/node:20-alpine \
#     --build-arg NGINX_IMAGE=swr.cn-north-4.myhuaweicloud.com/ddn-k8s/docker.io/nginx:alpine \
#     --build-arg NPM_REGISTRY=https://registry.npmmirror.com \
#     -t buddhist-text-frontend frontend/
ARG NODE_IMAGE=node:20-alpine
ARG NGINX_IMAGE=nginx:alpine
ARG NPM_REGISTRY=https://registry.npmjs.org


# ----- Development stage -----
FROM ${NODE_IMAGE} AS development

WORKDIR /app

ARG NPM_REGISTRY
RUN npm config set registry "${NPM_REGISTRY}"

COPY package*.json ./
RUN npm install

COPY . .

EXPOSE 3000

CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]


# ----- Build stage -----
FROM ${NODE_IMAGE} AS build

WORKDIR /app

ARG NPM_REGISTRY
RUN npm config set registry "${NPM_REGISTRY}"

COPY package*.json ./
RUN npm ci

COPY . .

# 跳过 tsc 前置（类型检查由 CI 守门），直接走 vite build。
RUN npx vite build


# ----- Production stage -----
FROM ${NGINX_IMAGE} AS production

COPY nginx.conf /etc/nginx/conf.d/default.conf
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
