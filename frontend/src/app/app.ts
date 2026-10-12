import { Component, ChangeDetectorRef } from '@angular/core';
import { HttpClient } from '@angular/common/http';
import { HttpClientModule } from '@angular/common/http';
import { FormsModule } from '@angular/forms';
import { CommonModule } from '@angular/common';
@Component({
  selector: 'app-root',
  standalone: true,
  imports: [HttpClientModule, FormsModule, CommonModule],
  templateUrl: './app.html',
  styleUrl: './app.css'
})

export class App {
  sessionId = crypto.randomUUID();
  selectedFile: File | null = null;
  question = '';
  answer = '';
  sources: any[] = [];
  loading = false;
  documentName = '';
  totalChunks = 0;
  characters = 0;
  uploaded = false;
  chatHistory: {
  question: string;
  answer: string;
}[] = [];

  clearChat() {

  this.question = "";
  this.answer = "";
  this.sources = [];
  this.chatHistory = [];

}
  constructor(
  private http: HttpClient,
  private cdr: ChangeDetectorRef
) {}
  askQuestion() {

  this.answer = "🤔 Thinking...";
  this.loading = true;

  this.http.post<any>(
    "http://127.0.0.1:8000/chat",
    {
      session_id: this.sessionId,
      question: this.question
    }
  ).subscribe({
    next: (response) => {

  this.answer = response.answer;
  this.chatHistory.push({
  question: this.question,
  answer: response.answer
});

this.question = "";
  this.sources = response.sources;
  this.loading = false;

  this.cdr.detectChanges();

},
    error: (error) => {

  console.error(error);

  this.answer = "❌ Unable to process your request. Please try again.";

  this.loading = false;

} 
  });

}
  onFileSelected(event: Event) {

  const input = event.target as HTMLInputElement;

  if (input.files && input.files.length > 0) {
    this.selectedFile = input.files[0];
    console.log(this.selectedFile);
  }

}

  uploadPdf() {

  if (!this.selectedFile) {
    alert("Please select a PDF first");
    return;
  }

  const formData = new FormData();
  formData.append("file", this.selectedFile);

  this.http.post(
    "http://127.0.0.1:8000/upload",
    formData
  ).subscribe({
    next: (response: any) => {

  console.log(response);

  this.documentName = response.filename;
  this.totalChunks = response.total_chunks;

  if (response.characters) {
    this.characters = response.characters;
  }

  this.uploaded = true;

  alert("PDF uploaded successfully!");

},
    error: (error) => {
      console.error(error);
      alert("Upload failed");
    }
  });

}

}
