import { useEffect, useState } from "react";
import { useAuthStore } from "@/stores/authStore";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Tabs, TabsList, TabsTrigger, TabsContent } from "@/components/ui/tabs";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";
import { authAPI } from "@/lib/api";
import type { User } from "@/types";

interface EditProfileModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
}

export function EditProfileModal({ open, onOpenChange }: EditProfileModalProps) {
  const { user, setUser } = useAuthStore();

  // keep local state in sync when modal opens/when user changes
  const [firstName, setFirstName] = useState<string>(user?.first_name ?? "");
  const [lastName, setLastName] = useState<string>(user?.last_name ?? "");
  const [email, setEmail] = useState<string>(user?.email ?? "");
  const [loading, setLoading] = useState(false);

  // password fields
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");

  useEffect(() => {
    // when modal opens or user changes, re-sync initial values
    if (open) {
      setFirstName(user?.first_name ?? "");
      setLastName(user?.last_name ?? "");
      setEmail(user?.email ?? "");
    }
  }, [open, user]);

  const handleSaveProfile = async () => {
    if (!user) return toast.error("No user found");

    try {
      setLoading(true);

      const payload = {
        email: email,
        firstname: firstName,
        lastname: lastName
      };

      // authAPI.updateProfile returns the updated user object (unwrapped)
      const apiUser = await authAPI.updateProfile(user.id, payload);

      // Transform backend fields → frontend User type
      const updatedUser: User = {
        id: apiUser.id,
        email: apiUser.email,
        first_name: apiUser.firstname,
        last_name: apiUser.lastname,
      };

      toast.success("Profile updated!");
      setUser(updatedUser);

      onOpenChange(false);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to update profile");
    } finally {
      setLoading(false);
    }
  };

  const handleChangePassword = async () => {
    if (!currentPassword || !newPassword) {
      toast.error("Enter both current and new password");
      return;
    }

    try {
      setLoading(true);
      const res = await authAPI.changePassword(currentPassword, newPassword);
      // res is AppResponse; show backend message if available
      toast.success(res.message || "Password updated!");
      setCurrentPassword("");
      setNewPassword("");
      onOpenChange(false);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Password change failed");
    } finally {
      setLoading(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-[95%] sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Edit Profile</DialogTitle>
        </DialogHeader>

        <Tabs defaultValue="profile" className="w-full mt-2">
          <TabsList className="grid grid-cols-2 w-full">
            <TabsTrigger value="profile">Profile</TabsTrigger>
            <TabsTrigger value="password">Password</TabsTrigger>
          </TabsList>

          {/* PROFILE TAB */}
          <TabsContent value="profile">
            <div className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>First Name</Label>
                <Input value={firstName} onChange={(e) => setFirstName(e.target.value)} />
              </div>

              <div className="space-y-2">
                <Label>Last Name</Label>
                <Input value={lastName} onChange={(e) => setLastName(e.target.value)} />
              </div>

              <div className="space-y-2">
                <Label>Email</Label>
                <Input value={email} onChange={(e) => setEmail(e.target.value)} />
              </div>

              <Button className="w-full gradient-cinematic glow-primary" disabled={loading} onClick={handleSaveProfile}>
                {loading ? "Saving..." : "Save Changes"}
              </Button>
            </div>
          </TabsContent>

          {/* PASSWORD TAB */}
          <TabsContent value="password">
            <div className="space-y-4 mt-4">
              <div className="space-y-2">
                <Label>Current Password</Label>
                <Input type="password" value={currentPassword} onChange={(e) => setCurrentPassword(e.target.value)} />
              </div>

              <div className="space-y-2">
                <Label>New Password</Label>
                <Input type="password" value={newPassword} onChange={(e) => setNewPassword(e.target.value)} />
              </div>

              <Button className="w-full gradient-cinematic glow-primary" disabled={loading} onClick={handleChangePassword}>
                {loading ? "Updating..." : "Update Password"}
              </Button>
            </div>
          </TabsContent>
        </Tabs>
      </DialogContent>
    </Dialog>
  );
}

export default EditProfileModal;
