import type { Metadata } from "next";
import { InstitutionalPage } from "@/components/layout/InstitutionalPage";

export const metadata: Metadata = {
  title: "Transparência de Afiliados",
  description:
    "Como funcionam os links de afiliados do Echonomiza e nossa política de comissões.",
};

export default function TransparenciaPage() {
  return (
    <InstitutionalPage eyebrow="Transparência" title="Transparência de Afiliados">
      <p>
        A Echonomiza participa de programas de afiliados de marketplaces. Quando
        você clica em “Ver na loja” e conclui uma compra, podemos receber uma
        comissão — sem aumentar o preço que você paga.
      </p>
      <p>
        Essa remuneração ajuda a manter a infraestrutura, os conectores e a
        curadoria de ofertas. Ela não altera nossa lógica de ranking: desconto,
        reputação e popularidade são calculados de forma independente.
      </p>
      <p>
        Sempre exibimos um aviso global de afiliados e reforçamos o aviso nas
        páginas de detalhe da oferta. Se tiver dúvidas, fale conosco pelos canais
        institucionais.
      </p>
    </InstitutionalPage>
  );
}
