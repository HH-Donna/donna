export const getCompanyLogoSources = (domain: string, companyName: string) => {
  const cleanDomain = domain.replace(/^https?:\/\//, '').replace(/^www\./, '').split('/')[0]
  
  const cleanCompanyName = companyName
    .toLowerCase()
    .replace(/[^a-z0-9\s]/g, '') 
    .replace(/\s+/g, '') 
  
  return [
    `https://logo.clearbit.com/${cleanDomain}`,
    `https://www.google.com/s2/favicons?domain=${cleanDomain}&sz=128`,
    `https://www.google.com/s2/favicons?domain=${cleanDomain}&sz=64`,
    `https://${cleanDomain}/favicon.ico`,
    `https://${cleanDomain}/favicon.png`,
    `https://logo.clearbit.com/${cleanCompanyName}.com`,
    `https://icons.duckduckgo.com/ip3/${cleanDomain}.ico`,
  ]
}

export const getLogoDisplayName = (companyName: string) => {
  const words = companyName.split(' ')
  if (words.length > 1) {
    return words.slice(0, 2).map(word => word[0]).join('').toUpperCase()
  }
  return companyName.slice(0, 2).toUpperCase()
}
