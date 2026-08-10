import { redirect } from "next/navigation";

export default function ReceivedQuoteRedirect() {
  redirect("/cotizacion?intent=received_quote");
}