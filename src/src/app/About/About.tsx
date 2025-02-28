import * as React from 'react';
import {
  Card,
  CardTitle,
  CardBody,
  Title,
  DescriptionList,
  DescriptionListGroup,
  DescriptionListTerm,
  DescriptionListDescription,
  PageSection,
} from '@patternfly/react-core';

export interface ISupportProps {
  sampleProp?: string;
}

// eslint-disable-next-line prefer-const
let About: React.FunctionComponent<ISupportProps> = () => (
  <PageSection hasBodyWrapper={true}>
    <Card isLarge>
        <CardTitle>
          <Title headingLevel="h4" size="xl">
            About the application
          </Title>
        </CardTitle>
        <CardBody>
          <DescriptionList>
            <DescriptionListGroup>
              <DescriptionListTerm>Author</DescriptionListTerm>
              <DescriptionListDescription>
                Milan Pospisil
              </DescriptionListDescription>
              <DescriptionListDescription>
                <a href="#">MilanPospisil</a>
              </DescriptionListDescription>
            </DescriptionListGroup>
            <DescriptionListGroup>
              <DescriptionListTerm>Repository</DescriptionListTerm>
              <DescriptionListDescription><a href="#">TODO</a></DescriptionListDescription>
            </DescriptionListGroup>
            <DescriptionListGroup>
              <DescriptionListTerm>Version</DescriptionListTerm>
              <DescriptionListDescription>1.0.0</DescriptionListDescription>
            </DescriptionListGroup>
          </DescriptionList>
        </CardBody>
      </Card>
  </PageSection>
);

export { About };
