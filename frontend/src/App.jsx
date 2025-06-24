import { BrowserRouter, Routes, Route } from "react-router-dom";
import SearchPage from "./pages/SearchPage";
import FileViewer from "./pages/FileViewer";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<SearchPage />} />
        <Route path="/view" element={<FileViewer />} />
      </Routes>
    </BrowserRouter>
  );
}
