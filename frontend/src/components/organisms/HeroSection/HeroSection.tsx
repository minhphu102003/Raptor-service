import { Button, Badge } from '@heroui/react'
import { Container, Text, Heading, Flex, Section } from '@radix-ui/themes'
import { ArrowRightIcon } from '@radix-ui/react-icons'
import { StatsGrid } from '../../molecules'
import { heroData } from '../../../constants/heroData'

interface HeroSectionProps {
  className?: string
}

export const HeroSection = ({ className }: HeroSectionProps) => {
  return (
    <Section className={`py-20 lg:py-32 ${className || ''}`}>
      <Container size="4">
        <div className="text-center max-w-4xl mx-auto">
          <Badge 
            color="primary" 
            variant="flat" 
            className="mb-6 px-3 py-1"
          >
            {heroData.badge}
          </Badge>
          
          <Heading 
            size="9" 
            className="text-gray-900 mb-6 bg-gradient-to-r from-gray-900 via-indigo-800 to-purple-800 bg-clip-text text-transparent"
          >
            {heroData.title}
          </Heading>
          
          <Text 
            size="5" 
            className="text-gray-600 mb-8 leading-relaxed max-w-2xl mx-auto"
          >
            {heroData.description}
          </Text>
          
          <Flex align="center" justify="center" gap="4" className="mb-12">
            <Button 
              size="lg" 
              color="primary" 
              className="font-semibold px-8 py-3"
              endContent={<ArrowRightIcon className="w-4 h-4" />}
            >
              {heroData.primaryButton.text}
            </Button>
            <Button 
              size="lg" 
              variant="bordered" 
              className="font-semibold px-8 py-3"
            >
              {heroData.secondaryButton.text}
            </Button>
          </Flex>
          
          <StatsGrid stats={heroData.stats} />
        </div>
      </Container>
    </Section>
  )
}