import type { Metadata } from "next";
import { InstitutionalPage } from "@/components/layout/InstitutionalPage";

export const metadata: Metadata = {
  title: "Sobre",
  description: "Conheça o FazOEco, portal automatizado de ofertas e afiliados.",
};

export default function SobrePage() {
  return (
    <InstitutionalPage eyebrow="Institucional" title="Sobre o FazOEco">
      <p>
        O FazOEco é um portal automatizado de ofertas e afiliados. Coletamos
        preços de marketplaces parceiros, calculamos descontos reais e ranqueamos
        produtos com base em qualidade, popularidade e reputação.
      </p>
      <p>
        Nosso objetivo é ajudar você a encontrar boas oportunidades com
        transparência — sempre deixando claro quando um link é de afiliado.
      </p>
      <p>
        A curadoria combina motores de precificação, faixas dinâmicas de desconto
        e validação humana no painel administrativo antes da publicação.
      </p>
    </InstitutionalPage>
  );
}
