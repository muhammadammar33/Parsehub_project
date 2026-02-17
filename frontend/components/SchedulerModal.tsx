"use client";

import { useState } from "react";
import Modal from "./Modal";

interface SchedulerModalProps {
  projectToken: string;
  onClose: () => void;
  onSchedule: (scheduledTime: string) => void;
}

export default function SchedulerModal({
  projectToken,
  onClose,
  onSchedule,
}: SchedulerModalProps) {
  const [scheduleType, setScheduleType] = useState<"once" | "recurring">(
    "once",
  );
  const [date, setDate] = useState("");
  const [time, setTime] = useState("");
  const [frequency, setFrequency] = useState<"daily" | "weekly" | "monthly">(
    "daily",
  );
  const [dayOfWeek, setDayOfWeek] = useState("monday");
  const [loading, setLoading] = useState(false);

  const handleSchedule = async () => {
    if (!date || !time) {
      alert("Please select both date and time");
      return;
    }

    setLoading(true);
    try {
      const scheduledDateTime = `${date}T${time}`;

      const response = await fetch("/api/projects/schedule", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          projectToken,
          scheduleType,
          scheduledTime: scheduledDateTime,
          frequency: scheduleType === "recurring" ? frequency : undefined,
          dayOfWeek:
            scheduleType === "recurring" && frequency === "weekly"
              ? dayOfWeek
              : undefined,
        }),
      });

      if (response.ok) {
        alert(`✅ Scheduled successfully for ${scheduledDateTime}`);
        onSchedule(scheduledDateTime);
        onClose();
      } else {
        alert("Failed to schedule");
      }
    } catch (error) {
      console.error("Schedule error:", error);
      alert("Error scheduling run");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Modal isOpen={true} onClose={onClose} title="Schedule Run">
      <div className="space-y-6">
        {/* Schedule Type */}
        <div>
          <label className="block text-sm font-semibold text-slate-300 mb-3">
            Schedule Type
          </label>
          <div className="flex gap-2 bg-slate-800/50 backdrop-blur-sm rounded-lg p-1 border border-slate-700/50">
            <button
              onClick={() => setScheduleType("once")}
              className={`flex-1 py-2.5 px-3 rounded-md font-medium transition-all duration-200 ${
                scheduleType === "once"
                  ? "bg-gradient-to-r from-purple-600 to-purple-500 text-white shadow-lg shadow-purple-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
              }`}
            >
              Run Once
            </button>
            <button
              onClick={() => setScheduleType("recurring")}
              className={`flex-1 py-2.5 px-3 rounded-md font-medium transition-all duration-200 ${
                scheduleType === "recurring"
                  ? "bg-gradient-to-r from-purple-600 to-purple-500 text-white shadow-lg shadow-purple-500/20"
                  : "text-slate-400 hover:text-slate-200 hover:bg-slate-700/50"
              }`}
            >
              Recurring
            </button>
          </div>
        </div>

        {/* Date & Time */}
        <div className="grid grid-cols-2 gap-4">
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Date
            </label>
            <input
              type="date"
              value={date}
              onChange={(e) => setDate(e.target.value)}
              className="w-full px-3 py-2.5 bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 text-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all"
            />
          </div>
          <div>
            <label className="block text-sm font-semibold text-slate-300 mb-2">
              Time
            </label>
            <input
              type="time"
              value={time}
              onChange={(e) => setTime(e.target.value)}
              className="w-full px-3 py-2.5 bg-slate-900/50 backdrop-blur-sm border border-slate-700/50 text-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all"
            />
          </div>
        </div>

        {/* Recurring Options */}
        {scheduleType === "recurring" && (
          <div className="space-y-4 p-4 bg-gradient-to-br from-purple-900/20 to-purple-800/10 backdrop-blur-sm border border-purple-500/30 rounded-lg">
            <div>
              <label className="block text-sm font-semibold text-slate-300 mb-2">
                Frequency
              </label>
              <select
                value={frequency}
                onChange={(e) => setFrequency(e.target.value as any)}
                className="w-full px-3 py-2.5 bg-slate-900/70 backdrop-blur-sm border border-slate-700/50 text-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all appearance-none cursor-pointer"
              >
                <option value="daily" className="bg-slate-900">
                  Daily
                </option>
                <option value="weekly" className="bg-slate-900">
                  Weekly
                </option>
                <option value="monthly" className="bg-slate-900">
                  Monthly
                </option>
              </select>
            </div>

            {frequency === "weekly" && (
              <div>
                <label className="block text-sm font-semibold text-slate-300 mb-2">
                  Day of Week
                </label>
                <select
                  value={dayOfWeek}
                  onChange={(e) => setDayOfWeek(e.target.value)}
                  className="w-full px-3 py-2.5 bg-slate-900/70 backdrop-blur-sm border border-slate-700/50 text-slate-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500/50 focus:border-purple-500/50 transition-all appearance-none cursor-pointer"
                >
                  <option value="monday" className="bg-slate-900">
                    Monday
                  </option>
                  <option value="tuesday" className="bg-slate-900">
                    Tuesday
                  </option>
                  <option value="wednesday" className="bg-slate-900">
                    Wednesday
                  </option>
                  <option value="thursday" className="bg-slate-900">
                    Thursday
                  </option>
                  <option value="friday" className="bg-slate-900">
                    Friday
                  </option>
                  <option value="saturday" className="bg-slate-900">
                    Saturday
                  </option>
                  <option value="sunday" className="bg-slate-900">
                    Sunday
                  </option>
                </select>
              </div>
            )}
          </div>
        )}

        {/* Buttons */}
        <div className="flex gap-3 pt-2">
          <button
            onClick={onClose}
            className="flex-1 px-4 py-2.5 border border-slate-700/50 text-slate-300 rounded-lg hover:bg-slate-800/50 hover:text-slate-100 font-medium transition-all duration-200 backdrop-blur-sm"
          >
            Cancel
          </button>
          <button
            onClick={handleSchedule}
            disabled={loading}
            className="flex-1 px-4 py-2.5 bg-gradient-to-r from-purple-600 to-purple-500 hover:from-purple-500 hover:to-purple-400 disabled:from-slate-700 disabled:to-slate-600 disabled:text-slate-400 text-white rounded-lg font-medium transition-all duration-200 shadow-lg shadow-purple-500/20 hover:shadow-purple-400/30 hover:scale-105 disabled:hover:scale-100 disabled:hover:shadow-none"
          >
            {loading ? "Scheduling..." : "Schedule"}
          </button>
        </div>
      </div>
    </Modal>
  );
}
