FROM golang:1.21-alpine AS builder

WORKDIR /app

# Install git and ca-certificates
RUN apk add --no-cache git ca-certificates

# Copy source code first
COPY . .

# Tidy up module dependencies and download
RUN go mod tidy

# Build the application
RUN CGO_ENABLED=0 GOOS=linux go build -a -installsuffix cgo -o main cmd/main.go

FROM alpine:latest

RUN apk --no-cache add ca-certificates postgresql-client tzdata

# Ensure timezone data is available
ENV TZ=UTC

WORKDIR /root/

# Copy the binary from builder
COPY --from=builder /app/main .

# Copy wait-for-postgres script
COPY wait-for-postgres.sh .
RUN chmod +x wait-for-postgres.sh

EXPOSE 8080

CMD ["./main"]