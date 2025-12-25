import { redirect } from "next/navigation";

export default function Home() {
  // Redirect to login page by default
  // In a real app, we would check authentication status here
  redirect("/login");
}
