import type { Metadata } from "next";
import "./globals.css";
export const metadata:Metadata={title:"MediCare AI Hospital Management System",description:"Secure patient management and AI-assisted clinical triage platform."};
export default function RootLayout({children}:{children:React.ReactNode}){return <html lang="en"><body>{children}</body></html>}
