import type { Metadata } from "next";
import { InstitutionalPage } from "@/components/layout/InstitutionalPage";

export const metadata: Metadata = {
  title: "Política de Privacidade",
};

export default function PrivacidadePage() {
  return (
    <InstitutionalPage eyebrow="Legal" title="Política de Privacidade">
      <p>
        Levamos a sério a proteção dos seus dados. O front-end público prioriza
        páginas estáticas/ISR e não exige cadastro para navegar pelas ofertas.
      </p>
      <p>
        Podemos coletar dados técnicos mínimos (como logs de acesso e métricas
        agregadas) para melhorar desempenho e segurança. Informações enviadas em
        formulários futuros serão tratadas conforme a LGPD.
      </p>
      <p>
        Links de afiliados podem registrar cookies ou parâmetros de rastreio no
        domínio da loja parceira. Consulte também as políticas desses sites.
      </p>
    </InstitutionalPage>
  );
}
