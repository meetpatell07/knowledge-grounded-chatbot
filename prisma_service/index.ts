import express from "express";
import { PrismaClient } from '@prisma/client';
import cors from 'cors';

const prisma = new PrismaClient();
const app = express();

// Enable CORS
app.use(cors({
  origin: ['http://localhost:3000', 'http://127.0.0.1:3000'],
  credentials: true
}));

app.use(express.json());

// Health check endpoint
app.get("/health", async (_req, res) => {
  try {
    await prisma.$connect();
    res.json({ status: "ok", database: "connected" });
  } catch (error: any) {
    res.status(500).json({ status: "error", error: error.message });
  }
});

// Get all sessions
app.get("/sessions", async (_req, res) => {
  try {
    const sessions = await prisma.session.findMany({
      include: { messages: true },
      orderBy: { createdAt: "desc" }
    });
    res.json(sessions);
  } catch (error: any) {
    console.error("Error fetching sessions:", error);
    res.status(500).json({ error: error.message || "Failed to fetch sessions" });
  }
});

// Get messages by session ID
app.get("/sessions/:id/messages", async (req, res) => {
  try {
    const msgs = await prisma.message.findMany({
      where: { sessionId: req.params.id },
      orderBy: { createdAt: "asc" }
    });
    res.json(msgs);
  } catch (error: any) {
    console.error("Error fetching messages:", error);
    res.status(500).json({ error: error.message || "Failed to fetch messages" });
  }
});

// Create or get session
app.post("/sessions", async (req, res) => {
  const { sessionId } = req.body;
  try {
    // Try to find existing session
    let session = await prisma.session.findUnique({
      where: { id: sessionId }
    });
    
    // If session doesn't exist, create it
    if (!session) {
      session = await prisma.session.create({
        data: { id: sessionId }
      });
    } else {
      // Update lastActive timestamp
      session = await prisma.session.update({
        where: { id: sessionId },
        data: { lastActive: new Date() }
      });
    }
    res.json(session);
  } catch (error: any) {
    console.error("Error creating/updating session:", error);
    res.status(500).json({ error: error.message });
  }
});

// Manual message insert (if frontend posts directly)
app.post("/messages", async (req, res) => {
  const { sessionId, role, content, source } = req.body;
  
  if (!sessionId || !role || !content) {
    return res.status(400).json({ error: "sessionId, role, and content are required" });
  }

  try {
    // Ensure session exists first
    let session = await prisma.session.findUnique({
      where: { id: sessionId }
    });
    
    if (!session) {
      // Create session if it doesn't exist
      session = await prisma.session.create({
        data: { id: sessionId }
      });
    } else {
      // Update lastActive timestamp
      await prisma.session.update({
        where: { id: sessionId },
        data: { lastActive: new Date() }
      });
    }

    // Now create the message
    const msg = await prisma.message.create({
      data: { sessionId, role, content, source }
    });
    res.json(msg);
  } catch (error: any) {
    console.error("Error creating message:", error);
    res.status(500).json({ error: error.message });
  }
});

app.listen(4000, () => console.log("Prisma service running on :4000"));
