import { redirect } from "next/navigation";

export default function DraftQuoteRedirect() {
  redirect("/cotizacion?intent=sending_quote");
}