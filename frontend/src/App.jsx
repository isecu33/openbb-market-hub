import { Routes, Route } from "react-router-dom";
import Layout from "@/components/Layout";
import Dashboard from "@/pages/Dashboard";
import Portfolio from "@/pages/Portfolio";
import Watchlist from "@/pages/Watchlist";
import News from "@/pages/News";
import Analysis from "@/pages/Analysis";
import Performance from "@/pages/Performance";
import Suggestions from "@/pages/Suggestions";
import Alerts from "@/pages/Alerts";
import Research from "@/pages/Research";
import ImportPage from "@/pages/Import";

export default function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<Dashboard />} />
        <Route path="/cartera" element={<Portfolio />} />
        <Route path="/watchlist" element={<Watchlist />} />
        <Route path="/noticias" element={<News />} />
        <Route path="/analisis" element={<Analysis />} />
        <Route path="/rendimiento" element={<Performance />} />
        <Route path="/sugerencias" element={<Suggestions />} />
        <Route path="/alertas" element={<Alerts />} />
        <Route path="/research" element={<Research />} />
        <Route path="/importar" element={<ImportPage />} />
      </Routes>
    </Layout>
  );
}
