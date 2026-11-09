import type { Metadata } from "next";
import { InstitutionalPage } from "@/components/layout/InstitutionalPage";

export const metadata: Metadata = {
  title: "Termos de Uso",
};

export default function TermosPage() {
  return (
    <InstitutionalPage eyebrow="Legal" title="Termos de Uso">
      <p>
        Ao utilizar o FazOEco, você concorda em usar o conteúdo apenas para fins
        informativos de comparação de ofertas. Não vendemos produtos diretamente.
      </p>
      <p>
        Preços, estoque e condições comerciais são de responsabilidade das lojas
        parceiras e podem mudar a qualquer momento. Sempre confira os dados no
        site do vendedor antes de concluir a compra.
      </p>
      <p>
        É proibido automatizar scrapers não autorizados contra este site, tentar
        burlar mecanismos de segurança ou republicar nosso conteúdo sem
        autorização.
      </p>
    </InstitutionalPage>
  );
}
