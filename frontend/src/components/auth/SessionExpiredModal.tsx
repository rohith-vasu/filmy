import React, { useEffect } from "react";
import { useAuthStore } from "@/stores/authStore";
import { useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

const SessionExpiredModal = () => {
  const show = useAuthStore((s) => s.showSessionExpired);
  const hide = useAuthStore((s) => s.hideSessionExpiredModal);
  const navigate = useNavigate();

  useEffect(() => {
    if (show) {
      // auto redirect after short delay
      const t = setTimeout(() => {
        hide();
        navigate("/login");
      }, 3000);
      return () => clearTimeout(t);
    }
  }, [show, hide, navigate]);

  return (
    <Dialog open={show} onOpenChange={(open) => { if (!open) hide(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Session expired</DialogTitle>
        </DialogHeader>

        <div className="py-2">
          <p>Your session has expired. You'll be redirected to the login page.</p>
        </div>

        <div className="flex justify-end">
          <Button onClick={() => { hide(); navigate("/login"); }}>
            Go to Login
          </Button>
        </div>
      </DialogContent>
    </Dialog>
  );
};

export default SessionExpiredModal;
