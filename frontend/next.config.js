/** @type {import('next').NextConfig} */
const optimizedHosts = [
  "m.media-amazon.com",
  "images-na.ssl-images-amazon.com",
  "images-eu.ssl-images-amazon.com",
  "http2.mlstatic.com",
  "cf.shopee.com.br",
  "down-br.img.susercontent.com",
];

const nextConfig = {
  reactStrictMode: true,
  output: "standalone",
  poweredByHeader: false,
  images: {
    remotePatterns: optimizedHosts.map((hostname) => ({
      protocol: "https",
      hostname,
    })),
  },
};

module.exports = nextConfig;
