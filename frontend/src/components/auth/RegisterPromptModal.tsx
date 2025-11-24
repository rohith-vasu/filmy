import React from "react";
import { useAuthStore } from "@/stores/authStore";
import { useNavigate } from "react-router-dom";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";

const RegisterPromptModal = () => {
  const show = useAuthStore((s) => s.showRegisterPrompt);
  const close = useAuthStore((s) => s.closeRegisterPrompt);
  const navigate = useNavigate();

  const goRegister = () => {
    close();
    navigate("/register");
  };

  return (
    <Dialog open={show} onOpenChange={(open) => { if (!open) close(); }}>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Account not found</DialogTitle>
        </DialogHeader>

        <div className="py-2">
          <p>
            We couldn't find an account for that email. Would you like to create one?
          </p>
        </div>

        <DialogFooter className="flex gap-2">
          <Button variant="ghost" onClick={close}>Cancel</Button>
          <Button onClick={goRegister}>Register</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
};

export default RegisterPromptModal;
