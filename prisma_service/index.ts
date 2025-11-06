import express from "express";
import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();
const app = express();
app.use(express.json());

// Get all sessions
app.get("/sessions", async (_req, res) => {
  const sessions = await prisma.session.findMany({
    include: { messages: true },
    orderBy: { createdAt: "desc" }
  });
  res.json(sessions);
});

// Get messages by session ID
app.get("/sessions/:id/messages", async (req, res) => {
  const msgs = await prisma.message.findMany({
    where: { sessionId: req.params.id },
    orderBy: { createdAt: "asc" }
  });
  res.json(msgs);
});

// Manual message insert (if frontend posts directly)
app.post("/messages", async (req, res) => {
  const { sessionId, role, content, source } = req.body;
  const msg = await prisma.message.create({
    data: { sessionId, role, content, source }
  });
  res.json(msg);
});

app.listen(4000, () => console.log("Prisma service running on :4000"));
