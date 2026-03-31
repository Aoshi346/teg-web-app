"use client";

import React, { useState, useEffect, useRef } from "react";
import { MessageSquare, Send } from "lucide-react";
import { Comment } from "@/types/project";
import { getComments, createComment } from "@/features/projects/projectService";
import { getUser } from "@/features/auth/clientAuth";

interface CommentsSectionProps {
  projectId: number;
}

export default function CommentsSection({ projectId }: CommentsSectionProps) {
  const [comments, setComments] = useState<Comment[]>([]);
  const [newComment, setNewComment] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [isSending, setIsSending] = useState(false);
  const commentsEndRef = useRef<HTMLDivElement>(null);
  const currentUser = getUser();

  const fetchComments = async () => {
    try {
      const data = await getComments(projectId);
      // Map ApiComment to Comment
      const mapped: Comment[] = data.map((c) => ({
        id: c.id,
        project: c.project,
        author: c.author,
        authorName: c.author_name,
        content: c.content,
        createdAt: c.created_at,
      }));
      setComments(mapped);
    } catch (error) {
      console.error("Error fetching comments:", error);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    fetchComments();
    // Poll for new comments every 10 seconds? Or just on mount.
    // For now just on mount.
    const interval = setInterval(fetchComments, 10000);
    return () => clearInterval(interval);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [projectId]);

  useEffect(() => {
    // Scroll to bottom on new comments
    commentsEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [comments]);

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newComment.trim()) return;

    setIsSending(true);
    try {
      await createComment(projectId, newComment.trim());
      setNewComment("");
      await fetchComments(); // Refresh list
    } catch (error) {
      console.error("Error sending comment:", error);
    } finally {
      setIsSending(false);
    }
  };

  const formatDate = (dateString: string) => {
    try {
      const date = new Date(dateString);
      return new Intl.DateTimeFormat("es-ES", {
        day: "numeric",
        month: "short",
        hour: "numeric",
        minute: "numeric",
        hour12: true,
      }).format(date);
    } catch {
      return "";
    }
  };

  // If user is neither Student, Tutor nor Admin, maybe hide?
  // Current logic: Tutors can see their projects (filtered by backend).
  // Students see theirs.
  // Comments should be visible to anyone who can see the project.

  return (
    <div className="bg-white rounded-2xl shadow-sm border border-gray-100 overflow-hidden mt-8 flex flex-col h-[500px]">
      <div className="p-4 border-b border-gray-100 flex items-center justify-between bg-gray-50/50">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-5 h-5 text-indigo-500" />
          <h3 className="font-bold text-gray-800">Comentarios y Discusión</h3>
        </div>
        <span className="text-xs font-medium text-gray-500 bg-white px-2 py-1 rounded-full border border-gray-200">
          {comments.length} mensajes
        </span>
      </div>

      {/* Comments List */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 bg-gray-50/30">
        {isLoading ? (
          <div className="flex justify-center py-10">
            <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-indigo-500"></div>
          </div>
        ) : comments.length === 0 ? (
          <div className="text-center py-10 text-gray-400">
            <MessageSquare className="w-12 h-12 mx-auto mb-2 opacity-20" />
            <p className="text-sm">No hay comentarios aún.</p>
            <p className="text-xs">
              Inicia la conversación con tu tutor o estudiante.
            </p>
          </div>
        ) : (
          comments.map((comment) => {
            const isMe = comment.author === currentUser?.id;
            const formattedDate = formatDate(comment.createdAt);

            return (
              <div
                key={comment.id}
                className={`flex gap-3 ${isMe ? "flex-row-reverse" : "flex-row"}`}
              >
                <div className={`flex-shrink-0 mt-1`}>
                  <div
                    className={`w-8 h-8 rounded-full flex items-center justify-center text-xs font-bold text-white shadow-sm ${isMe ? "bg-indigo-500" : "bg-gray-400"}`}
                  >
                    {comment.authorName.charAt(0).toUpperCase()}
                  </div>
                </div>
                <div
                  className={`max-w-[80%] rounded-2xl p-3 shadow-sm ${
                    isMe
                      ? "bg-indigo-600 text-white rounded-tr-none"
                      : "bg-white border border-gray-200 text-gray-800 rounded-tl-none"
                  }`}
                >
                  <div
                    className={`flex items-baseline justify-between gap-4 mb-1 border-b ${isMe ? "border-indigo-500/30 pb-1" : "border-gray-100 pb-1"}`}
                  >
                    <span
                      className={`text-xs font-bold ${isMe ? "text-indigo-100" : "text-gray-900"}`}
                    >
                      {comment.authorName}
                    </span>
                    <span
                      className={`text-[10px] ${isMe ? "text-indigo-200" : "text-gray-400"}`}
                    >
                      {formattedDate}
                    </span>
                  </div>
                  <p className="text-sm whitespace-pre-wrap leading-relaxed">
                    {comment.content}
                  </p>
                </div>
              </div>
            );
          })
        )}
        <div ref={commentsEndRef} />
      </div>

      {/* Input Area */}
      <form
        onSubmit={handleSend}
        className="p-4 bg-white border-t border-gray-100"
      >
        <div className="relative flex items-center gap-2">
          <input
            type="text"
            value={newComment}
            onChange={(e) => setNewComment(e.target.value)}
            placeholder="Escribe un mensaje..."
            className="flex-1 pl-4 pr-12 py-3 bg-gray-50 border border-gray-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-indigo-500/20 focus:border-indigo-500 transition-all text-sm"
            disabled={isSending}
          />
          <button
            type="submit"
            disabled={!newComment.trim() || isSending}
            className="absolute right-2 p-2 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors shadow-sm"
          >
            {isSending ? (
              <div className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
