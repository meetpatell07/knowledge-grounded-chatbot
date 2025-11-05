import { defineConfig, env } from "prisma/config";
import dotenv from "dotenv";
import path from "path";

// Load .env from prisma_service directory first (local overrides)
dotenv.config({ path: path.resolve(__dirname, ".env") });

// Load .env from backend directory (shared/common config)
// This allows using the same .env file as Python code
dotenv.config({ path: path.resolve(__dirname, "../.env") });

export default defineConfig({
  schema: "prisma/schema.prisma",
  migrations: {
    path: "prisma/migrations",
  },
  engine: "classic",
  datasource: {
    url: env("DATABASE_URL"),
  },
});
